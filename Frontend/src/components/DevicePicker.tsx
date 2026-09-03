import { Avatar, Description, Label, ListBox, type Selection } from "@heroui/react";
import { urlVarsAtom } from "../utils/atoms";
import { useAtom } from "jotai";

interface Device {
  id: string;
  name: string;
  model: string;
}

interface DevicePickerProps extends React.ComponentProps<typeof ListBox> {
  devices: Device[];
}

export function DevicePicker(props: Readonly<DevicePickerProps>) {
  const { className, devices, ...otherProps } = props;
  const [urlVars, setUrlVars] = useAtom(urlVarsAtom);

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