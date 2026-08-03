import { MainHeaderProps } from "../confs/main-header";

export default function MainHeader({
  titleIcon,
  title,
  subtitle,
  actionButton,
}: MainHeaderProps) {
  return (
    <div className="flex justify-between gap-4 w-full items-center flex-wrap p-6">
      <div className="flex flex-col space-y-1.5 p-0">
        <h3 className="font-semibold tracking-tight text-xl flex flex-row gap-2">
          {titleIcon} {title}
        </h3>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>
      {actionButton && <div>{actionButton}</div>}
    </div>
  );
}
