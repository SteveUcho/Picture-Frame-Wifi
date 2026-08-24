import { useAtomValue } from "jotai";
import { urlVarsAtom, selectedDeviceAtom } from "../utils/atoms";
import { Form, TextField, Label, Input, FieldError, Description, Button, ScrollShadow, Select, ListBox } from "@heroui/react";
import { fetchWithBackend } from "../utils/fetch";

interface CustomFormProps extends React.HTMLAttributes<HTMLFormElement> {
  submitURL: string;
}

export function CustomForm(props: Readonly<CustomFormProps>) {
  const { children, submitURL, ...rest } = props;
  const selectedDevice = useAtomValue(selectedDeviceAtom);
  const urlVars = useAtomValue(urlVarsAtom);

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
    fetchWithBackend(apiPath, {
      method: "POST",
      body: JSON.stringify(jsonBody)
    });
  };

  // TODO: Submit pull request to move heroui from using deprecated React.FormEvent to React.SubmitEvent
  return (
    <>
    {
      !selectedDevice && (
        <div className="absolute flex items-center justify-center bg-gray-600/50 z-10 h-full w-full -m-8 rounded-xl">
          <p>Please select a device first</p>
        </div>
      )
    }
      <Form className="flex flex-col gap-2 w-full flex-1 min-h-0" onSubmit={handleSubmit as any}>
        <ScrollShadow className="flex flex-col gap-2 flex-1">
          <TextField
            name="sleepInterval"
            type="text"
            variant="secondary"
          >
            <Label>Sleep Interval</Label>
            <Input placeholder="00:00:00" />
            <Description>Format: HH:MM:SS</Description>
            <FieldError />
          </TextField>
          <Select fullWidth placeholder="Select orientation" variant="secondary">
            <Label>Orientation</Label>
            <Select.Trigger>
              <Select.Value />
              <Select.Indicator />
            </Select.Trigger>
            <Select.Popover>
              <ListBox>
                <ListBox.Item id="horizontal" textValue="Horizontal">
                  Horizontal
                  <ListBox.ItemIndicator />
                </ListBox.Item>
                <ListBox.Item id="vertical" textValue="Vertical">
                  Vertical
                  <ListBox.ItemIndicator />
                </ListBox.Item>
              </ListBox>
            </Select.Popover>
            <Description>Options: horizontal, vertical</Description>
          </Select>
        </ScrollShadow>
        <div className="flex gap-2">
          <Button type="submit" className="flex-1">
            Submit
          </Button>
          <Button type="reset" variant="secondary">
            Reset
          </Button>
        </div>
      </Form>
    </>

  );
}