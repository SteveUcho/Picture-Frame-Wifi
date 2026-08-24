import { useAtomValue } from "jotai";
import { urlVarsAtom } from "../utils/atoms";
import { Form, TextField, Label, Input, FieldError, Description, Button, ScrollShadow, Select, ListBox, type Key } from "@heroui/react";
import { fetchWithBackend } from "../utils/fetch";
import { useState } from "react";

interface CustomFormProps {
  submitURL: string;
}

export function CustomForm(props: Readonly<CustomFormProps>) {
  const { submitURL } = props;
  const urlVars = useAtomValue(urlVarsAtom);
  const [formState, setFormState] = useState<Record<string, string | number>>({});
  // TODO: Get current form state from backend

  const handleSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    let apiPath = submitURL;
    for (const [key, value] of Object.entries(urlVars)) {
      apiPath = apiPath.replace(`:${key}`, value);
    }
    fetchWithBackend(apiPath, {
      method: "POST",
      body: JSON.stringify(formState)
    });
    console.log(apiPath, formState);
  };

  const handleKeyChange = (key: string, initial: Key | null) => (value: Key | null) => {
    if (value === null || value === initial) {
      const newFormState = { ...formState };
      delete newFormState[key];
      setFormState(newFormState);
    } else {
      setFormState(prev => ({
        ...prev,
        [key]: value
      }));
    }
  };

  // TODO: Submit pull request to move heroui from using deprecated React.FormEvent to React.SubmitEvent
  return (
    <>
      {
        !urlVars.deviceId && (
          <div className="absolute flex items-center justify-center bg-gray-800/80 z-10 h-full w-full -m-8 rounded-xl">
            <p>Please select a device first</p>
          </div>
        )
      }
      <Form
        className="flex flex-col gap-2 w-full flex-1 min-h-0"
        onSubmit={handleSubmit as any}
      >
        <ScrollShadow className="flex flex-col gap-2 flex-1">
          <TextField
            name="sleepInterval"
            type="text"
            variant="secondary"
            value={formState.sleepInterval as string || ""}
            onChange={handleKeyChange("sleepInterval", "")}
          >
            <Label>Sleep Interval</Label>
            <Input
              placeholder="00:00:00"
            />
            <Description>Format: HH:MM:SS</Description>
            <FieldError />
          </TextField>
          <Select
            fullWidth
            name="orientation"
            placeholder="Select orientation"
            variant="secondary"
            value={formState.orientation || ""}
            onChange={handleKeyChange("orientation", "")}
          >
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
          {/* TODO: Add loading state + error handling + success feedback + fade back to disabled after success */}
          <Button isDisabled={!Object.keys(formState).length} type="submit" className="flex-1">
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