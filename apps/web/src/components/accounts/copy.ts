import type { Locale } from "@/components/sites/simplywall-st-1b042a47/shared/i18n/messages";

const messages = {
  zh: {
    home: "返回首页", login: "登录", register: "创建账户", email: "邮箱", password: "密码",
    welcome: "欢迎回来", join: "建立你的研究工作台", intro: "登录后管理你的关注公司。",
    registration: "使用邮箱创建 TradeAgent 账户。", passwordHint: "密码须为 12–128 个字符。",
    pending: "正在处理…", noAccount: "还没有账户？", haveAccount: "已有账户？",
    workspace: "研究工作台", logout: "退出登录", refresh: "重新加载", search: "搜索公司或股票代码",
    companies: "公司目录", watchlist: "我的关注", follow: "关注", unfollow: "取消关注",
    loading: "正在加载…", empty: "暂无关注公司，从公司目录添加。",
    noCompanies: "数据库中未找到匹配公司。", connected: "已连接数据库", retry: "重试",
    footer: "TradeAgent · 个人研究空间", note: "这里展示数据库中的公司与个人关注，不代表实时行情。",
    errors: {
      invalid_credentials: "邮箱或密码不正确。", email_unavailable: "此邮箱已注册，请登录。",
      invalid_auth_input: "请填写有效邮箱，注册密码须为 12–128 个字符。",
      origin_not_allowed: "当前访问地址未获允许，请使用本地预览地址。",
      too_many_attempts: "尝试次数过多，请稍后再试。", authentication_required: "登录已失效，请重新登录。",
      backend_unavailable: "暂时无法连接服务，请稍后重试。", company_not_found: "该公司已不可用，请刷新目录。",
      unknown: "操作未完成，请重试。",
    },
  },
  en: {
    home: "Back to home", login: "Sign in", register: "Create account", email: "Email", password: "Password",
    welcome: "Welcome back", join: "Build your research workspace", intro: "Sign in to manage your followed companies.",
    registration: "Create a TradeAgent account with your email.", passwordHint: "Use 12–128 characters for your password.",
    pending: "Working…", noAccount: "New to TradeAgent?", haveAccount: "Already have an account?",
    workspace: "Research workspace", logout: "Sign out", refresh: "Reload", search: "Search a company or ticker",
    companies: "Company directory", watchlist: "Following", follow: "Follow", unfollow: "Unfollow",
    loading: "Loading…", empty: "You are not following any companies yet. Add one from the directory.",
    noCompanies: "No matching companies were found in the database.", connected: "Connected to database", retry: "Retry",
    footer: "TradeAgent · Your research space", note: "Companies and your follows come from the database. This is not a live market feed.",
    errors: {
      invalid_credentials: "The email or password is incorrect.", email_unavailable: "This email is registered. Please sign in.",
      invalid_auth_input: "Enter a valid email and a registration password of 12–128 characters.",
      origin_not_allowed: "This address is not allowed. Use the local preview address.",
      too_many_attempts: "Too many attempts. Please try again later.", authentication_required: "Your session expired. Please sign in again.",
      backend_unavailable: "The service is unavailable. Please try again shortly.", company_not_found: "This company is unavailable. Refresh the directory.",
      unknown: "The action could not be completed. Please try again.",
    },
  },
};

export function accountCopy(locale: Locale) { return messages[locale]; }
export function accountError(locale: Locale, code: string) {
  const errors: Record<string, string> = messages[locale].errors;
  return Object.hasOwn(errors, code) ? errors[code] : errors.unknown;
}

export async function readApiError(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json();
    if (data && typeof data === "object" && "detail" in data && typeof data.detail === "string") return data.detail;
  } catch { /* Error bodies may be empty after a network interruption. */ }
  return "unknown";
}
