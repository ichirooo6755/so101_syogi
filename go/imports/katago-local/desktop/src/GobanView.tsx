import { useLayoutEffect, useRef, useState } from "react";
import { Goban, type GobanProps } from "@sabaki/shudan";

export const MIN_VERTEX_SIZE = 20;

/** Resizing changes a single scale, never the board dimensions or aspect ratio. */
export function GobanView(props: Omit<GobanProps, "vertexSize">) {
  const frame = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState(1);

  useLayoutEffect(() => {
    const element = frame.current;
    if (!element) return;
    const resize = (width: number, height: number) => {
      if (width > 0 && height > 0) {
        setSize(Math.max(1, Math.min(760, Math.floor(width), Math.floor(height))));
      }
    };
    const style = getComputedStyle(element);
    resize(
      element.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight),
      element.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom),
    );
    const observer = new ResizeObserver(([entry]) => resize(entry.contentRect.width, entry.contentRect.height));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const square = props.signMap.length > 0 && props.signMap.every((row) => row.length === props.signMap.length);
  // Shudan adds .25em padding and .15em border on each side. Calculate the
  // final cell size directly so a previous maximum cannot affect shrinkage.
  const vertexSize = Math.max(MIN_VERTEX_SIZE, Math.min(38, Math.floor(size / (props.signMap.length + 0.8))));
  return <div className="goban-frame" ref={frame} role="region" aria-label="碁盤" tabIndex={0}>
    {square ? <Goban {...props} vertexSize={vertexSize} /> : <p role="alert">正方形の盤面を選択してください。</p>}
  </div>;
}
