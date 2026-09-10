"""表格检测与透视变换校正模块
负责定位原图中试卷练习表格的四个角点，并执行透视校正，同时提供网格定位和坐标双向映射。
"""

import cv2
import numpy as np


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

    # 1. 过滤贯穿全图的孤立非表格竖线 (如相邻页边缘、装订线，高度超过 82% 图像高)
    num_v, labels_v, stats_v, _ = cv2.connectedComponentsWithStats(v_lines)
    for idx in range(1, num_v):
        lh = stats_v[idx, cv2.CC_STAT_HEIGHT]
        if lh > small_h * 0.82:
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

    return order_points(safe_corners)


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
