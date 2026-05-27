import api from "./api.js";

export async function uploadFile(consultationId, file) {
  const formData = new FormData();
  formData.append("consultation_id", consultationId);
  formData.append("file", file);
  const res = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function getConsultationFiles(consultationId) {
  const res = await api.get(`/upload/consultation/${consultationId}`);
  return res.data.files;
}

export async function deleteFile(fileId) {
  const res = await api.delete(`/upload/file/${fileId}`);
  return res.data;
}

export function getFileUrl(fileId) {
  return `${import.meta.env.VITE_API_URL || ""}/api/upload/file/${fileId}`;
}
