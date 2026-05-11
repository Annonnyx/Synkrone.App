"use client";

export function LogoMosaicBg() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
      style={{
        backgroundImage: `url("/images/Logo.png")`,
        backgroundSize: "60px 60px",
        backgroundRepeat: "repeat",
        transform: "rotate(45deg) scale(1.5)",
        opacity: 0.06,
        filter: "sepia(1) saturate(5) hue-rotate(20deg) brightness(0.7) grayscale(0.2)",
        width: "150vw",
        height: "150vh",
        left: "-25vw",
        top: "-25vh",
      }}
    />
  );
}
