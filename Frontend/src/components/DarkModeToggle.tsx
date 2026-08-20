import { useAtom } from "jotai";
import { Switch } from "@heroui/react";
import { darkModeAtom } from "../utils/atoms";

export function DarkModeToggle() {
  const [isDark, setIsDark] = useAtom(darkModeAtom);

  const handleToggle = () => {
    setIsDark(prev => !prev);
    document.documentElement.classList.toggle('dark', !isDark);
  };

  return (
    <Switch isSelected={isDark} onChange={handleToggle} aria-label="Dark mode" size="lg">
          {({isSelected}) => (
            <Switch.Content>
              <Switch.Control className={isSelected ? "bg-blue-500" : "bg-gray-300"}>
                <Switch.Thumb>
                  <Switch.Icon>
                    {isSelected ? (
                      <span className="text-inherit opacity-70">🌙</span>
                    ) : (
                      <span className="text-inherit opacity-100">☀️</span>
                    )}
                  </Switch.Icon>
                </Switch.Thumb>
              </Switch.Control>
            </Switch.Content>
          )}
        </Switch>
  );
}