#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { createCipheriv, randomBytes } from "node:crypto";
import { deflateSync } from "node:zlib";

const POST_URL = "https://json.excalidraw.com/api/v2/post/";
const EXCALIDRAW_URL = "https://excalidraw.com/";

function base64url(buffer) {
  return Buffer.from(buffer)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function concatBuffers(...buffers) {
  const versionBytes = 4;
  const lengthBytes = 4;
  const totalLength =
    versionBytes +
    buffers.length * lengthBytes +
    buffers.reduce((sum, buffer) => sum + buffer.byteLength, 0);
  const output = Buffer.alloc(totalLength);
  let cursor = 0;
  output.writeUInt32BE(1, cursor);
  cursor += versionBytes;
  for (const buffer of buffers) {
    output.writeUInt32BE(buffer.byteLength, cursor);
    cursor += lengthBytes;
    Buffer.from(buffer).copy(output, cursor);
    cursor += buffer.byteLength;
  }
  return output;
}

function encryptAndCompress(data, key) {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-128-gcm", key, iv);
  const compressed = deflateSync(data);
  const encrypted = Buffer.concat([cipher.update(compressed), cipher.final(), cipher.getAuthTag()]);
  return { iv, encrypted };
}

function createPayload(scene) {
  const key = randomBytes(16);
  const encryptionKey = base64url(key);
  const databaseScene = {
    type: scene.type || "excalidraw",
    version: scene.version || 2,
    source: scene.source || "https://excalidraw.com",
    elements: scene.elements || [],
    appState: scene.appState || {},
  };
  const dataBuffer = Buffer.from(JSON.stringify(databaseScene, null, 2), "utf8");
  const encodingMetadata = Buffer.from(
    JSON.stringify({ version: 2, compression: "pako@1", encryption: "AES-GCM" }),
    "utf8",
  );
  const contentsMetadata = Buffer.from("null", "utf8");
  const contents = concatBuffers(contentsMetadata, dataBuffer);
  const { iv, encrypted } = encryptAndCompress(contents, key);
  return {
    encryptionKey,
    payload: concatBuffers(encodingMetadata, iv, encrypted),
  };
}

async function main() {
  const input = process.argv[2];
  if (!input) {
    console.error("usage: share_excalidraw.mjs <scene.excalidraw>");
    process.exit(2);
  }

  const scene = JSON.parse(await readFile(input, "utf8"));
  const { encryptionKey, payload } = createPayload(scene);
  const response = await fetch(POST_URL, { method: "POST", body: payload });
  const result = await response.json();
  if (!response.ok || !result.id) {
    throw new Error(`Excalidraw upload failed: ${response.status} ${JSON.stringify(result)}`);
  }
  console.log(`${EXCALIDRAW_URL}#json=${result.id},${encryptionKey}`);
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
