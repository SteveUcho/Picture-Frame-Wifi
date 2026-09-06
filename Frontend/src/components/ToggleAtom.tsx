import { useSetAtom } from "jotai";
import type { PrimitiveAtom } from "jotai";
import { cloneElement, type ReactElement } from "react";

interface ToggleAtomProps<T> {
  atom: PrimitiveAtom<T>;
  toggleValue: T;
  children: ReactElement<{ onClick?: () => void }>;
}

export function ToggleAtom<T>(props: Readonly<ToggleAtomProps<T>>) {
  const { atom, children, toggleValue } = props;
  const setValue = useSetAtom(atom);

  const newElement = cloneElement(children, {
    onClick: () => setValue(toggleValue),
  });

  return newElement;
}