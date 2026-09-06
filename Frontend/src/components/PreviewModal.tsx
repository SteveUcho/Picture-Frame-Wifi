import { Modal, Button } from "@heroui/react";
import { toggleModalAtom, urlVarsAtom } from "../utils/atoms";
import { useAtom } from "jotai";
import { useEffect, useState } from "react";
import { fetchWithBackend } from "../utils/fetch";
import { Picture } from "@gravity-ui/icons";

export function PreviewModal() {
  const [urlVars] = useAtom(urlVarsAtom);
  const [modalState, setModalState] = useAtom(toggleModalAtom);
  const [image, setImage] = useState<number[]>([]);

  useEffect(() => {
    if (modalState.id === "previewModal" && image.length === 0) {
      getImageBuffer();
      drawImage();
    } else if (modalState.id === "previewModal" && image.length > 0) {
      drawImage();
    }
  }, [modalState.id, image.length]);

  const colorMap: Record<number, string> = {
    0: "black",
    1: "white",
    2: "yellow",
    3: "red",
    4: "",
    5: "blue",
    6: "green",
  };

  const getImageBuffer = async () => {
    const response = await fetchWithBackend("/getFrameBuffer/" + urlVars.deviceId);
    // 1. Read the response body as an ArrayBuffer
    const buffer = await response.arrayBuffer();

    // 2. Create a Uint8Array view to look at the data byte by byte
    const byteArray = new Uint8Array(buffer);

    // Array to hold our converted integers (each will be 0 to 15)
    const image = [];

    for (const element of byteArray) {
      const byte = element;

      // 1. Get the first 4 bits (Shift right by 4 places)
      const highNibble = byte >> 4;

      // 2. Get the last 4 bits (Mask with 00001111)
      const lowNibble = byte & 0x0F;

      image.push(highNibble, lowNibble);
    }
    // Output array of integers between 0 and 15
    setImage(image);
  }

  const drawImage = () => {
    const canvas = document.getElementById("preview-canvas") as HTMLCanvasElement;
    const ctx = canvas.getContext("2d");

    if (ctx) {
      let x = 0;
      let y = 0;
      for (const pixel of image) {
        ctx.fillStyle = colorMap[pixel];
        ctx.fillRect(x, y, 1, 1);
        x++;
        if (x >= 800) {
          x = 0;
          y++;
        }
      }
    }
  };

  const handleRefresh = () => {
    getImageBuffer();
    drawImage();
  };

  const handleClose = () => {
    setModalState({});
    setImage([]);
  };

  return (
    <Modal.Backdrop isOpen={modalState.id === "previewModal"} onOpenChange={handleClose}>
      <Modal.Container size="cover">
        <Modal.Dialog>
          <Modal.CloseTrigger />
          <Modal.Header>
            <Modal.Icon className="bg-accent-soft text-accent-soft-foreground">
              <Picture className="size-5" />
            </Modal.Icon>
            <Modal.Heading>Preview</Modal.Heading>
          </Modal.Header>
          <Modal.Body>
            <div className="flex h-full items-center">
              <div className="flex-1">
                <canvas id="preview-canvas" width="800" height="480" className="w-full"></canvas>
              </div>
            </div>
          </Modal.Body>
          <Modal.Footer>
            <Button slot="close" variant="secondary">
              Cancel
            </Button>
            <Button onClick={handleRefresh}>
              Refresh
            </Button>
          </Modal.Footer>
        </Modal.Dialog>
      </Modal.Container>
    </Modal.Backdrop>
  );
}