"""表格检测与透视变换校正模块
负责定位原图中试卷练习表格的四个角点，并执行透视校正，同时提供网格定位和坐标双向映射。
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger("math-grader")


def order_points(pts: np.ndarray) -> np.ndarray:
    """对四个角点进行排序：[左上, 右上, 右下, 左下]"""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]       # top-left
    rect[2] = pts[np.argmax(s)]       # bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]    # top-right
    rect[3] = pts[np.argmax(diff)]    # bottom-left
    return rect


def detect_table_corners(img: np.ndarray, max_dim: int = 1200) -> np.ndarray:
    """检测输入图片中的表格四个顶点。
    具备断线自修复、孤立贯穿线过滤和表头顶边安全自适应防护。

    返回：
        np.ndarray: shape (4, 2)，在原始分辨率下的 4 个角点 [TL, TR, BR, BL]
    """
    h, w = img.shape[:2]
    scale = float(max_dim) / max(h, w)
    small_w, small_h = int(w * scale), int(h * scale)
    small = cv2.resize(img, (small_w, small_h))

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    inv_blur = cv2.bitwise_not(blur)
    thresh = cv2.adaptiveThreshold(
        inv_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2
    )

    # 形态学提取水平线与垂直线
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(small_w / 25), 1))
    h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)

    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(small_h / 35)))
    v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 1. 过滤贯穿全图的孤立非表格竖线 (如相邻页边缘、装订线，高度超过 85% 图像高且与水平网格线几乎无交点)
    num_v, labels_v, stats_v, _ = cv2.connectedComponentsWithStats(v_lines)
    for idx in range(1, num_v):
        lh = stats_v[idx, cv2.CC_STAT_HEIGHT]
        if lh > small_h * 0.85:
            comp_mask = (labels_v == idx).astype(np.uint8) * 255
            intersections = cv2.bitwise_and(comp_mask, h_lines)
            num_inter, _, _, _ = cv2.connectedComponentsWithStats(intersections)
            # 真正的表格纵向线至少会与 15+ 条水平线相交；交点极少（少于 4 个）才判定为孤立杂线
            if (num_inter - 1) < 4:
                v_lines[labels_v == idx] = 0

    table_grid = cv2.bitwise_or(h_lines, v_lines)

    # 寻找最大外接轮廓
    contours, _ = cv2.findContours(table_grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        margin_x, margin_y = int(w * 0.05), int(h * 0.05)
        return np.array([
            [margin_x, margin_y],
            [w - margin_x, margin_y],
            [w - margin_x, h - margin_y],
            [margin_x, h - margin_y]
        ], dtype="float32")

    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    best_cnt = contours[0]
    hull = cv2.convexHull(best_cnt)
    peri = cv2.arcLength(hull, True)
    # 使用更细腻的逼近公差，避免粗公差折叠表头
    approx = cv2.approxPolyDP(hull, 0.012 * peri, True)

    if len(approx) == 4:
        pts = approx.reshape(-1, 2) / scale
    else:
        rect = cv2.minAreaRect(best_cnt)
        box = cv2.boxPoints(rect)
        pts = box / scale

    corners = order_points(pts)
    TL, TR, BR, BL = corners

    # 2. 检查左右边长度比例，防止单侧连到整张纸边缘
    len_L = np.linalg.norm(TL - BL)
    len_R = np.linalg.norm(TR - BR)
    if len_R > len_L * 1.25:
        TR = BR + (TL - BL)
        corners[1] = TR
    elif len_L > len_R * 1.25:
        TL = BL + (TR - BR)
        corners[0] = TL

    # 3. 对称平衡的安全外扩，确保表头和底部第 20 行完全落在画幅内，避免上下失衡导致漏行
    tbl_h = max(np.linalg.norm(BL - TL), 100.0)
    tbl_w = max(np.linalg.norm(TR - TL), 100.0)
    up_vec_L = (TL - BL) / np.linalg.norm(TL - BL)
    up_vec_R = (TR - BR) / np.linalg.norm(TR - BR)
    left_vec = (TL - TR) / np.linalg.norm(TL - TR)
    right_vec = (TR - TL) / np.linalg.norm(TR - TL)

    # 采用上下对称 3.5% 的安全外扩，使表头顶线稳定在 70~80px，第 20 行底线稳定在 2160~2170px
    up_ext = 0.035 * tbl_h
    down_ext = 0.035 * tbl_h
    side_ext = 0.015 * tbl_w

    safe_TL = TL + up_vec_L * up_ext + left_vec * side_ext
    safe_TR = TR + up_vec_R * up_ext + right_vec * side_ext
    safe_BL = BL - up_vec_L * down_ext + left_vec * side_ext
    safe_BR = BR - up_vec_R * down_ext + right_vec * side_ext

    safe_corners = np.array([safe_TL, safe_TR, safe_BR, safe_BL], dtype="float32")
    safe_corners[:, 0] = np.clip(safe_corners[:, 0], 0, w - 1)
    safe_corners[:, 1] = np.clip(safe_corners[:, 1], 0, h - 1)

    ordered = order_points(safe_corners)
    return orient_table_corners(img, ordered)


def orient_table_corners(img: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """自动判定速算练习册表格的真实物理朝向，并在 4 个角点循环移位中选取最符合正向排版的顶点顺序。

    物理排版不变量：
    1. 21 个物理行在纵向产生约 52px (在 800x1100 评估图下) 的强烈自相关周期波峰 (横置时仅 ~0.05)；
    2. 全局最窄列为左侧“序号”列 (宽度约 4%~6%)，右侧各列为计算列 (宽度约 7%~12%)；
    3. 表头上部区域包含练习册大标题、日期等文字，外边距文字墨水密度显著高于表底空白留白区。

    返回：
        np.ndarray: 经过朝向纠正后的 4 个角点 [TL, TR, BR, BL] (shape 4x2)
    """
    candidates = []
    for shift in range(4):
        c_shifted = np.roll(corners, -shift, axis=0)
        # 采用 800x1100 快速透视变换以进行特征评分
        dst = np.array([[0, 0], [800, 0], [800, 1100], [0, 1100]], dtype="float32")
        M = cv2.getPerspectiveTransform(c_shifted.astype("float32"), dst)
        thumb = cv2.warpPerspective(img, M, (800, 1100))
        th_h, th_w = thumb.shape[:2]

        gray = cv2.cvtColor(thumb, cv2.COLOR_BGR2GRAY)
        inv = cv2.bitwise_not(gray)
        th = cv2.adaptiveThreshold(inv, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)

        # 1. 横向线条自相关：检测高度方向上 21 行周期性 (行距约为 1100 / 21 ≈ 52px)
        hk = cv2.getStructuringElement(cv2.MORPH_RECT, (int(th_w / 25), 1))
        h_lines = cv2.morphologyEx(th, cv2.MORPH_OPEN, hk)
        proj_h = np.sum(h_lines[:, int(th_w * 0.45):int(th_w * 0.95)], axis=1).astype(float)
        smooth_h = np.convolve(proj_h, np.ones(5) / 5, mode="same")
        norm_h = smooth_h - np.mean(smooth_h)
        autocorr = np.correlate(norm_h, norm_h, mode="full")[len(norm_h) - 1:]

        peak_val = 0.0
        if autocorr[0] > 0:
            peak_val = float(np.max(autocorr[40:65])) / float(autocorr[0])

        # 2. 竖向线条聚类：检测各列宽度分布，消除边缘假峰干扰
        vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        v_lines = cv2.morphologyEx(th, cv2.MORPH_OPEN, vk)
        proj_v = np.sum(v_lines[int(th_h * 0.25):int(th_h * 0.85), :], axis=0).astype(float)
        smooth_v = np.convolve(proj_v, np.ones(7) / 7, mode="same")

        # 过滤边缘 2% 杂线噪声后寻找显著波峰
        margin = int(th_w * 0.02)
        valid_range = smooth_v[margin:th_w - margin]
        peaks = []
        if np.max(valid_range) > 0:
            p_thresh = np.max(valid_range) * 0.25
            for x in range(margin + 5, th_w - margin - 5):
                if smooth_v[x] > p_thresh and smooth_v[x] == np.max(smooth_v[x - 8:x + 9]):
                    peaks.append(x)

        g_peaks = []
        for p in peaks:
            if not g_peaks or p - g_peaks[-1] > 20:
                g_peaks.append(p)
            else:
                g_peaks[-1] = (g_peaks[-1] + p) // 2

        col_score = 0.0
        if len(g_peaks) >= 4:
            col_widths = [g_peaks[i + 1] - g_peaks[i] for i in range(len(g_peaks) - 1)]
            valid_widths = [(idx, w) for idx, w in enumerate(col_widths) if 20 <= w <= 180]
            if valid_widths:
                # 全局最窄列分析
                min_col_idx = min(valid_widths, key=lambda x: x[1])[0]
                num_cols = len(col_widths)
                if min_col_idx <= max(1, num_cols // 4):
                    col_score = 2.0
                elif min_col_idx >= num_cols - 1 - max(1, num_cols // 4):
                    col_score = -2.0

                # 左前 2 列与右后 2 列平均宽度对比
                left_w = np.mean([w for _, w in valid_widths[:2]]) if len(valid_widths) >= 2 else 50
                right_w = np.mean([w for _, w in valid_widths[-2:]]) if len(valid_widths) >= 2 else 50
                if left_w < right_w * 0.85:
                    col_score += 1.5
                elif right_w < left_w * 0.85:
                    col_score -= 1.5

        # 3. 表头 vs 页脚外侧文字非网格墨水密度不对称性
        text_mask = cv2.bitwise_and(th, cv2.bitwise_not(cv2.bitwise_or(h_lines, v_lines)))
        top_band = text_mask[15:75, int(th_w * 0.1):int(th_w * 0.9)]
        bot_band = text_mask[th_h - 75:th_h - 15, int(th_w * 0.1):int(th_w * 0.9)]
        top_ink = np.sum(top_band > 0)
        bot_ink = np.sum(bot_band > 0)
        hdr_score = 0.0
        if top_ink > bot_ink * 1.25:
            hdr_score = 1.0
        elif bot_ink > top_ink * 1.25:
            hdr_score = -1.0

        # 综合评分：若行周期波峰过低，说明并非竖版排版，严重惩罚
        if peak_val < 0.12:
            total_score = -50.0 + peak_val * 10.0
        else:
            total_score = peak_val * 10.0 + col_score * 2.0 + hdr_score * 1.5

        candidates.append((shift, total_score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    best_shift = candidates[0][0]
    best_score = candidates[0][1]
    rot_desc = {0: "正向 (0°)", 1: "顺时针90°", 2: "上下颠倒 (180°)", 3: "逆时针90°"}.get(best_shift, f"移位{best_shift}")
    logger.info(f"[Table-Detect] 表格物理朝向判定完成: 识别为 {rot_desc}, 综合评分={best_score:.2f}, shift={best_shift}")
    return np.roll(corners, -best_shift, axis=0)


def warp_table(img: np.ndarray, corners: np.ndarray, target_w: int = 1600, target_h: int = 2200):
    """根据 4 个角点进行透视变换，生成展平的高清表格图，同时返回变换矩阵和逆变换矩阵。

    返回：
        warped_img: 展平后的表格图
        M: 原图 -> 展平图的变换矩阵 (3, 3)
        M_inv: 展平图 -> 原图的逆变换矩阵 (3, 3)
    """
    dst = np.array([
        [0, 0],
        [target_w - 1, 0],
        [target_w - 1, target_h - 1],
        [0, target_h - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(corners.astype("float32"), dst)
    M_inv = cv2.getPerspectiveTransform(dst, corners.astype("float32"))

    warped = cv2.warpPerspective(img, M, (target_w, target_h), flags=cv2.INTER_LANCZOS4)
    return warped, M, M_inv


def detect_grid_cells(warped_img: np.ndarray, total_rows: int = 21, total_cols: int = 11):
    """检测展平表格上的所有单元格网格坐标。
    第 0 行为表头，第 1~20 行为题目行。
    采用全局几何基准结合局部形态学吸附，防止手写笔迹切出假线导致行错位。

    返回：
        row_bounds: List of (y1, y2) 每行的上、下边界
        col_bounds: List of (x1, x2) 每列的左、右边界
    """
    h, w = warped_img.shape[:2]
    gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
    inv_gray = cv2.bitwise_not(gray)
    th = cv2.adaptiveThreshold(inv_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, -2)

    # 提取横向水平线（排除左侧手写密集区，统计中右侧以精准提取无笔迹干扰的表格横线）
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(w / 25), 1))
    h_lines = cv2.morphologyEx(th, cv2.MORPH_OPEN, h_kernel)
    proj = np.sum(h_lines[:, int(w * 0.45):int(w * 0.95)], axis=1).astype(float)
    smooth = np.convolve(proj, np.ones(5) / 5, mode='same')

    # 1. 一维自相关 (Autocorrelation) 精确测定网格固有物理行距 (通常为 90~115 像素)
    norm_s = smooth - np.mean(smooth)
    autocorr = np.correlate(norm_s, norm_s, mode='full')[len(smooth) - 1:]
    spacing = 80 + int(np.argmax(autocorr[80:130]))
    if spacing < 85 or spacing > 120:
        spacing = 100

    # 2. 寻找表格最底边 y_bottom (位于 2050~2190 像素区间的最显著波峰)
    bot_win = smooth[2050:min(h, 2190)]
    if len(bot_win) > 0 and np.max(bot_win) > 0:
        thresh_b = np.max(bot_win) * 0.3
        cands_b = [
            y for y in range(2050, min(h, 2190))
            if smooth[y] > thresh_b and smooth[y] == np.max(smooth[max(0, y - 10):min(h, y + 11)])
        ]
        y_bottom = cands_b[-1] if cands_b else (2050 + int(np.argmax(bot_win)))
    else:
        y_bottom = int(h * 0.985)

    # 3. 自底向上逆推严格的 21 个物理行 (20 个练习行 + 1 个表头行)
    # 表格下方为空白备注无干扰，从底边逆推 21 个周期彻底免疫顶部标题下划线的干扰，
    # 并以自相关行距 spacing 为引导在 ±12 像素窗口内精准吸附真实表格线。
    cuts_bottom_up = [y_bottom]
    curr_y = y_bottom
    for _ in range(total_rows):  # 21 步，形成 22 条切割线
        target_y = curr_y - spacing
        win_min = max(0, int(target_y - 12))
        win_max = min(h, int(target_y + 13))
        win = smooth[win_min:win_max]
        if len(win) > 0 and np.max(win) > np.max(smooth) * 0.05:
            prev_y = win_min + int(np.argmax(win))
        else:
            prev_y = target_y
        cuts_bottom_up.append(prev_y)
        curr_y = prev_y

    all_cuts = cuts_bottom_up[::-1]  # 从表头顶边到表格底边
    row_bounds = [(all_cuts[i], all_cuts[i + 1]) for i in range(len(all_cuts) - 1)]
    y_top = all_cuts[0]
    y_row1_top = all_cuts[1]

    # 提取列边界：优先采用表头区域垂直线聚类检测，自适应契合不同题型表格
    gray_hdr = cv2.cvtColor(warped_img[max(0, y_top):min(h, y_row1_top), :], cv2.COLOR_BGR2GRAY)
    inv_hdr = 255 - gray_hdr
    th_hdr = cv2.adaptiveThreshold(inv_hdr, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 35))
    v_lines = cv2.morphologyEx(th_hdr, cv2.MORPH_OPEN, v_kernel)
    v_proj = np.sum(v_lines, axis=0).astype(float)
    smooth_v = np.convolve(v_proj, np.ones(9) / 9, mode='same')

    thresh_v = np.max(smooth_v) * 0.15 if np.max(smooth_v) > 0 else 1.0
    clusters = []
    in_peak = False
    start_idx = 0
    for i in range(w):
        if smooth_v[i] > thresh_v:
            if not in_peak:
                in_peak = True
                start_idx = i
        else:
            if in_peak:
                in_peak = False
                best_x = start_idx + int(np.argmax(smooth_v[start_idx:i]))
                clusters.append(best_x)

    # 合并相邻距离小于 35 像素的双峰
    merged_cols = []
    for x in clusters:
        if not merged_cols:
            merged_cols.append(x)
        elif (x - merged_cols[-1]) < 35:
            merged_cols[-1] = int((merged_cols[-1] + x) / 2)
        else:
            merged_cols.append(x)

    if len(merged_cols) == total_cols + 1:
        col_bounds = [(merged_cols[j], merged_cols[j + 1]) for j in range(total_cols)]
    else:
        # 降级比例
        if total_cols == 11:
            standard_ratios = [0.052, 0.071, 0.071, 0.103, 0.072, 0.072, 0.100, 0.100, 0.125, 0.114, 0.120]
        else:
            standard_ratios = [1.0 / total_cols] * total_cols
        total_r = sum(standard_ratios)
        col_cuts = [0]
        cur_x = 0
        for r in standard_ratios:
            cur_x += (r / total_r) * w
            col_cuts.append(int(cur_x))
        col_cuts[-1] = w
        col_bounds = [(int(col_cuts[j]), int(col_cuts[j + 1])) for j in range(len(col_cuts) - 1)]

    logger.info(f"[Grid-Detect] 网格分割完成: 物理行距={spacing}px, 检测有效行={len(row_bounds)}, 有效列={len(col_bounds)}")
    return row_bounds, col_bounds


def transform_points(pts: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """使用 3x3 透视变换矩阵将点从一个坐标系投射到另一个坐标系。

    输入：
        pts: shape (N, 2)
        matrix: shape (3, 3)
    返回：
        transformed_pts: shape (N, 2)
    """
    pts_reshaped = pts.reshape(-1, 1, 2).astype("float32")
    transformed = cv2.perspectiveTransform(pts_reshaped, matrix)
    return transformed.reshape(-1, 2)
