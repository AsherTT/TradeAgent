"use client";

import { createContext, useContext } from "react";

export const WorkbenchLayoutContext = createContext(false);

export function useWorkbenchLayout() {
  return useContext(WorkbenchLayoutContext);
}
