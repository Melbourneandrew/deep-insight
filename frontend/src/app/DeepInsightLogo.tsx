interface DeepInsightLogoProps {
  size?: number;
  className?: string;
}

export default function DeepInsightLogo({
  size = 24,
  className = "",
}: DeepInsightLogoProps) {
  return (
    <svg
      fill="currentColor"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      id="research-left"
      data-name="Line Color"
      xmlns="http://www.w3.org/2000/svg"
      className={`icon line-color ${className}`}
    >
      <g id="SVGRepo_bgCarrier" strokeWidth={0} />

      <g
        id="SVGRepo_tracerCarrier"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <g id="SVGRepo_iconCarrier">
        <path
          id="secondary"
          d="M7,17V12m4,5V15M21,15l-2.83-2.83M13,10a3,3,0,1,0,3-3A3,3,0,0,0,13,10Z"
          style={{
            fill: "none",
            stroke: "#2a6dce",
            strokeLinecap: "round",
            strokeLinejoin: "round",
            strokeWidth: 2,
          }}
        />

        <path
          id="primary"
          d="M17,17v3a1,1,0,0,1-1,1H4a1,1,0,0,1-1-1V4A1,1,0,0,1,4,3H16"
          style={{
            fill: "none",
            stroke: "#000000",
            strokeLinecap: "round",
            strokeLinejoin: "round",
            strokeWidth: 2,
          }}
        />
      </g>
    </svg>
  );
}
