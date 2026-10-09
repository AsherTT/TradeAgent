import { LocalizedImage } from "./i18n/LanguageProvider";

export function TradeAgentLogo({ placement }: { placement: "header" | "footer" }) {
  return (
    <LocalizedImage
      src={placement === "header" ? "/tradeagent-header.svg" : "/tradeagent-footer.svg"}
      width="108"
      alt="TradeAgent"
      className={placement === "header" ? "logo-image" : "logo-image-2"}
    />
  );
}
