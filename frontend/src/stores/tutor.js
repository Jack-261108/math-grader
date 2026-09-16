import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getAiExplanation } from '../api/tutor';
import { useConfigStore } from './config';

export const useTutorStore = defineStore('tutor', () => {
  const configStore = useConfigStore();

  const isLoading = ref(false);
  const currentExplanation = ref(null);
  const errorMsg = ref('');

  async function askTutor(type, questionData, userQuery = '') {
    isLoading.value = true;
    errorMsg.value = '';
    currentExplanation.value = null;

    try {
      const fd = new FormData();
      fd.append('question_type', type);
      fd.append('question_info', JSON.stringify(questionData));
      if (userQuery?.trim()) {
        fd.append('user_query', userQuery.trim());
      }
      configStore.appendApiCredentials(fd);

      const res = await getAiExplanation(fd);
      currentExplanation.value = res.explanation || {
        core_cause: "错因分析详见下文秒杀秘籍。",
        speed_tricks: "善用截位直除与首位排除法。",
        pitfall_tips: "审清题干时间节点与增长率/增长量区别。",
        summary: "稳扎稳打，查漏补缺！"
      };
      return currentExplanation.value;
    } catch (err) {
      errorMsg.value = err.message || '获取名师解析失败';
      currentExplanation.value = {
        core_cause: `提示: ${err.message}`,
        speed_tricks: "【公考秒杀思维】：做题先看选项差距。若差距大于 10%，直接前两位截位直除排除 2 项；若差距较小再微调，切忌从头死算。",
        pitfall_tips: "考场中切勿在单道题纠缠超时，该蒙猜时果断根据选项平衡律抉择。",
        summary: "建议在右上角【⚙️ 设置】中配置个人 API Key 获取大模型深度解析！"
      };
    } finally {
      isLoading.value = false;
    }
  }

  return {
    isLoading,
    currentExplanation,
    errorMsg,
    askTutor
  };
});
