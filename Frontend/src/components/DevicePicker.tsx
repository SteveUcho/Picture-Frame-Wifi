import { Avatar, Description, Label, ListBox, type Selection } from "@heroui/react";
import { urlVarsAtom } from "../utils/atoms";
import { useAtom } from "jotai";
import { useEffect, useState } from "react";
import { fetchWithBackend } from "../utils/fetch";

interface Device {
  id: string;
  name: string;
  model: string;
}

export function DevicePicker(props: Readonly<React.ComponentProps<typeof ListBox>>) {
  const { className, ...otherProps } = props;
  const [devices, setDevices] = useState<Device[]>([{ id: "loading", name: "Loading...", model: "" }]);
  const [urlVars, setUrlVars] = useAtom(urlVarsAtom);

  useEffect(() => {
    // get devices from backend
    fetchWithBackend("/admin/getDevices")
      .then((response) => response.json())
      .then((data) => {
        setDevices(data);
      });
  }, []);

  const handleSlected = (selection: Selection) => {
    const value = Array.from(selection)[0];
    setUrlVars({ ...urlVars, deviceId: value as string });
  };

  return (
    <ListBox
      className={`w-full p-0 ${className}`}
      selectionMode="single"
      selectedKeys={urlVars.deviceId ? [urlVars.deviceId] : []}
      onSelectionChange={handleSlected}
      disabledKeys={["no-devices"]}
      {...otherProps}
    >
      {!devices.length && (
        <ListBox.Item key="no-devices" id="no-devices" textValue="No devices">
          <Description>No devices found</Description>
        </ListBox.Item>
      )}
      {devices.map((device) => (
        <ListBox.Item key={device.id} id={device.id} textValue={device.name}>
          <Avatar size="sm">
            <Avatar.Fallback>{device.name.charAt(0)}</Avatar.Fallback>
          </Avatar>
          <div className="flex flex-col">
            <Label>{device.name}</Label>
            <Description>{device.model}</Description>
          </div>
          <ListBox.ItemIndicator />
        </ListBox.Item>
      ))}
    </ListBox>
  );
}