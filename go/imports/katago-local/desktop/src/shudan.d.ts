declare module "@sabaki/shudan" {
  import type { ComponentType } from "react";

  export type Vertex = [number, number];
  export type Sign = -1 | 0 | 1;

  export interface Marker {
    type: "circle" | "cross" | "square" | "triangle" | "label";
    label?: string;
    tooltip?: string;
  }

  export interface GhostStone {
    sign: -1 | 1;
    type?: "good" | "interesting" | "doubtful" | "bad";
    faint?: boolean;
  }

  export interface HeatPoint {
    strength: number;
    text?: string;
  }

  export interface BoundedGobanProps {
    maxWidth?: number;
    maxHeight?: number;
    maxVertexSize?: number;
    signMap: Sign[][];
    markerMap?: (Marker | null)[][];
    ghostStoneMap?: (GhostStone | null)[][];
    heatMap?: (HeatPoint | null)[][];
    selectedVertices?: Vertex[];
    onVertexClick?: (event: unknown, vertex: Vertex) => void;
  }

  export const BoundedGoban: ComponentType<BoundedGobanProps>;
  export interface GobanProps extends Omit<BoundedGobanProps, "maxWidth" | "maxHeight" | "maxVertexSize"> {
    vertexSize?: number;
  }
  export const Goban: ComponentType<GobanProps>;
}
