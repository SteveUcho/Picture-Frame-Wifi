import { Modal, Button } from "@heroui/react";
import { toggleModalAtom, urlVarsAtom } from "../utils/atoms";
import { useAtom } from "jotai";
import { useEffect, useState } from "react";
import { fetchWithBackend, postWithBackend } from "../utils/fetch";
import { Picture } from "@gravity-ui/icons";

const unpackImageToArray = (byteArray: Uint8Array) => {
  const image: number[] = [];
  for (const element of byteArray) {
    const byte = element;
    const highNibble = byte >> 4;
    const lowNibble = byte & 0x0F;
    image.push(highNibble, lowNibble);
  }
  return image;
};

export function PreviewModal() {
  const [urlVars] = useAtom(urlVarsAtom);
  const [modalState, setModalState] = useAtom(toggleModalAtom);
  const [image, setImage] = useState<number[][]>([]);

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
    // First get the headers to ensure the frame is ready
    await fetchWithBackend("/v2/GetFrameHeaders/" + urlVars.deviceId);

    // Then get the image parts
    const response1 = await fetchWithBackend("/v2/GetFrameImage/" + urlVars.deviceId + "/part/0");
    const response2 = await fetchWithBackend("/v2/GetFrameImage/" + urlVars.deviceId + "/part/1");

    // Finally complete the image transfer
    await postWithBackend("/v2/CompleteFrameImage/" + urlVars.deviceId);

    // const response = await fetchWithBackend("/getFrameBuffer/" + urlVars.deviceId);
    // 1. Read the response body as an ArrayBuffer
    const buffer1 = await response1.arrayBuffer();
    const buffer2 = await response2.arrayBuffer();

    // 2. Create a Uint8Array view to look at the data byte by byte
    const byteArray1 = new Uint8Array(buffer1);
    const byteArray2 = new Uint8Array(buffer2);

    // Array to hold our converted integers (each will be 0 to 15)
    const image1: number[] = unpackImageToArray(byteArray1);
    const image2: number[] = unpackImageToArray(byteArray2);

    // Output array of integers between 0 and 15
    setImage([image1, image2]);
  }

  const drawImage = () => {
    const canvas = document.getElementById("preview-canvas") as HTMLCanvasElement;
    const ctx = canvas.getContext("2d");

    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (let i = 0; i < image.length; i++) {
        const slice = image[i];
        let x = 0;
        let y = 0;
        for (const pixel of slice) {
          ctx.fillStyle = colorMap[pixel];
          ctx.fillRect(x, y, 1, 1);
          x++;
          if (x >= (i + 1) * 600) {
            x = i * 600;
            y++;
          }
        }
      }
    }
  };

  const handleRefresh = async () => {
    await getImageBuffer();
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
                <canvas id="preview-canvas" width="1200" height="1600" className="w-full"></canvas>
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