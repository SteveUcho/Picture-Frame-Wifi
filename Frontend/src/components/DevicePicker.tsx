import { Avatar, Description, Label, ListBox } from "@heroui/react";

interface Device {
  id: string;
  name: string;
  model: string;
}

export const demoDevices: Device[] = [
  {
    id: "1",
    name: "Living Room",
    model: "small - 8"
  },
  {
    id: "2",
    name: "Bedroom",
    model: "large - 13"
  }
];

interface DevicePickerProps extends React.ComponentProps<typeof ListBox> {
  devices: Device[];
}

export function DevicePicker(props: Readonly<DevicePickerProps>) {
  const { devices, className, ...otherProps } = props;

  return (
    <ListBox className={`w-full p-0 ${className}`} selectionMode="single" {...otherProps}>
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