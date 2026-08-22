import { atom } from "jotai";
import { atomWithStorage } from "jotai/utils";

export const selectedDeviceAtom = atom<string | null>(null);
export const urlVarsAtom = atom<{ [key: string]: string }>({});
export const darkModeAtom = atomWithStorage<boolean>("darkMode", true);
