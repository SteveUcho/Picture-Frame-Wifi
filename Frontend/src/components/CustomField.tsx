import { useAtom } from "jotai";
import { urlVarsAtom } from "../utils/atoms";
import { formInput } from "../utils/classNames";

interface CustomFieldProps {
  name: string;
  label: string;
}

export function CustomField({ name, label }: CustomFieldProps) {
  const [urlVars, setUrlVars] = useAtom(urlVarsAtom);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrlVars({ ...urlVars, [name]: e.target.value });
  };

  return (
      <div>
          <label htmlFor={name}>{label}</label>
          <input type="text" id={name} name={name} onChange={handleChange} className={formInput} />
      </div>
  );
}