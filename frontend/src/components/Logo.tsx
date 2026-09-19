interface Props {
  size?: number;
  className?: string;
}

export function Logo({ size = 40, className }: Props) {
  return (
    <img
      src="/kdu_logo.png"
      alt="Koperativa Dezenvolvimentu Umanu"
      width={size}
      height={size}
      className={className ? `rounded-full ${className}` : "rounded-full"}
      style={{ objectFit: "contain" }}
    />
  );
}
