interface ChromagoraDemoFooterProps {
  text?: string;
  linkUrl?: string;
}

export default function ChromagoraDemoFooter({
  text = "Created at Chromagora by human minds",
  linkUrl = "https://chromagora.com",
}: ChromagoraDemoFooterProps) {
  return (
    <footer className="w-full py-8 text-center">
      <a
        href={linkUrl}
        className="inline-flex items-center justify-center gap-2 text-xs font-medium text-slate-500 hover:text-slate-800"
      >
        <span className="grid h-5 w-5 place-items-center rounded-full border border-slate-300 text-[13px] font-semibold">
          C
        </span>
        <span>{text}</span>
      </a>
    </footer>
  );
}
