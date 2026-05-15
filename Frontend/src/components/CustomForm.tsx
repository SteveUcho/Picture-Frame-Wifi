import { useAtomValue } from "jotai";
import { urlVarsAtom } from "../utils/atoms";

interface CustomFormProps extends React.HTMLAttributes<HTMLFormElement> {
  submitURL: string;
}

export function CustomForm(props: CustomFormProps) {
  const { children, submitURL, ...rest } = props;
  const urlVars = useAtomValue(urlVarsAtom);
  const apiUrl = import.meta.env.PUBLIC_API_URL;

  const handleSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    let apiPath = submitURL;
    for (const [key, value] of Object.entries(urlVars)) {
      apiPath = apiPath.replace(`:${key}`, value);
    }
    const jsonBody = Object.fromEntries(new FormData(e.currentTarget));
    // if empty string, unset the field
    for (const [key, value] of Object.entries(jsonBody)) {
      if (value === "") {
        delete jsonBody[key];
      }
    }
    fetch(apiUrl + apiPath, {
      method: "POST",
      body: JSON.stringify(jsonBody),
      headers: {
        "Content-Type": "application/json"
      }
    });
  };
  
  return (
      <form {...rest} onSubmit={handleSubmit} className="flex flex-col gap-4">
          {children}
      </form>
  );
}