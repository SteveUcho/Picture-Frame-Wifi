import { useAtomValue } from "jotai";
import { urlVarsAtom } from "../utils/atoms";
import { Form, TextField, Label, Input, FieldError, Description, Button, ScrollShadow, Select, ListBox, type Key, Spinner } from "@heroui/react";
import { fetchWithBackend, generateUrl, swrFetcher } from "../utils/fetch";
import { useState } from "react";
import useSWR from "swr";

interface CustomFormProps {
  submitURL: string;
  fetchURL: string;
}

interface FormData {
  "id"?: number;
  "name"?: string;
  "sleepInterval"?: string;
  "orientation"?: "horizontal" | "vertical";
  "size"?: number;
}

export function CustomForm(props: Readonly<CustomFormProps>) {
  const { submitURL, fetchURL } = props;
  const urlVars = useAtomValue(urlVarsAtom);
  const { data, isLoading, error, mutate } = useSWR<FormData>(generateUrl(fetchURL, urlVars), swrFetcher)
  const [formState, setFormState] = useState<FormData>({});

  const formData = { ...data, ...formState };

  const handleSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const apiPath = generateUrl(submitURL, urlVars);
    if (!apiPath) return;
    const options = {
      optimisticData: formData,
      rollbackOnError: (error: unknown) => {
        // If it's timeout abort error, don't rollback
        setFormState({ ...formState });
        return error instanceof Error && error.name !== 'AbortError'
      },
    }

    mutate(async () => {
      const res = await fetchWithBackend(apiPath, {
        method: "POST",
        body: JSON.stringify(formState)
      });

      if (!res.ok) {
        throw new Error('Failed to update data');
      }
      return formData;
    }, options);
    setFormState({});
  };

  const handleKeyChange = (key: keyof FormData) => (value: Key | null) => {
    if (value === null || value === data?.[key]) {
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

  return (
    <>
      {
        !urlVars.deviceId && (
          <div className="absolute flex items-center justify-center bg-default/80 z-10 h-full w-full -m-8 rounded-xl">
            <p>Please select a device first</p>
          </div>
        )
      }
      {
        isLoading && (
          <div className="absolute flex items-center justify-center bg-default-800/80 z-10 h-full w-full -m-8 rounded-xl">
            <Spinner />
          </div>
        )
      }
      {
        error && (
          <div className="absolute flex items-center justify-center bg-red-600/70 z-10 h-full w-full -m-8 rounded-xl">
            <p>Error: {error?.message}</p>
          </div>
        )
      }
      {/* TODO: Submit pull request to move heroui from using deprecated React.FormEvent to React.SubmitEvent to remove any type assertions */}
      <Form
        className="flex flex-col gap-2 w-full flex-1 min-h-0"
        onSubmit={handleSubmit as any}
      >
        <ScrollShadow className="flex flex-col gap-2 flex-1">
          <TextField
            name="name"
            type="text"
            variant="secondary"
            value={formData.name || ""}
            onChange={handleKeyChange("name")}
          >
            <Label>Name</Label>
            <Input
              placeholder="Frame Name"
            />
            <Description>Set the name of the frame</Description>
            <FieldError />
          </TextField>
          <TextField
            name="sleepInterval"
            type="text"
            variant="secondary"
            value={formData.sleepInterval || ""}
            onChange={handleKeyChange("sleepInterval")}
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
            value={formData.orientation || ""}
            onChange={handleKeyChange("orientation")}
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
          <Button isDisabled={!Object.keys(formState).length} type="submit" className="flex-1">
            Submit
          </Button>
          <Button type="button" variant="secondary" onPress={() => setFormState({})}>
            Reset
          </Button>
        </div>
      </Form>
    </>
  );
}