import React, { useState, useRef, useCallback } from "react";
import { Upload, X, FileText, Image, Trash2, Download, AlertCircle } from "lucide-react";
import { uploadFile, deleteFile, getFileUrl } from "../services/upload.js";
import { useToast } from "./ToastProvider.jsx";

const ALLOWED_TYPES = [
  "image/jpeg", "image/png", "image/gif", "application/pdf",
];
const MAX_SIZE_MB = 5;

export default function FileUploadZone({ consultationId, files, onChange, readOnly = false }) {
  const toast = useToast();
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewFile, setPreviewFile] = useState(null);

  const validateFile = (file) => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      toast.error("Only JPG, PNG, GIF, and PDF files are allowed.");
      return false;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      toast.error(`File too large. Max ${MAX_SIZE_MB}MB.`);
      return false;
    }
    return true;
  };

  const handleUpload = async (file) => {
    if (!validateFile(file)) return;
    setUploading(true);
    try {
      const res = await uploadFile(consultationId, file);
      toast.success("File uploaded successfully");
      onChange([...(files || []), res.file]);
    } catch (err) {
      toast.error(err.response?.data?.error || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    if (readOnly) return;
    const dropped = Array.from(e.dataTransfer.files);
    dropped.forEach(handleUpload);
  }, [readOnly, files]);

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!readOnly) setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleInputChange = (e) => {
    const selected = Array.from(e.target.files);
    selected.forEach(handleUpload);
    e.target.value = "";
  };

  const handleDelete = async (fileId) => {
    try {
      await deleteFile(fileId);
      toast.success("File deleted");
      onChange((files || []).filter((f) => f.id !== fileId));
      if (previewFile?.id === fileId) setPreviewFile(null);
    } catch (err) {
      toast.error(err.response?.data?.error || "Delete failed");
    }
  };

  const formatSize = (bytes) => {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const isImage = (mime) => mime?.startsWith("image/");

  return (
    <div className="space-y-3">
      {/* Upload zone */}
      {!readOnly && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => inputRef.current?.click()}
          className={`
            relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer
            transition-all duration-200
            ${dragOver
              ? "border-primary-500 bg-primary-50"
              : "border-slate-300 bg-slate-50 hover:border-primary-400 hover:bg-slate-100"
            }
            ${uploading ? "opacity-60 pointer-events-none" : ""}
          `}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.gif,.pdf"
            className="hidden"
            onChange={handleInputChange}
          />
          <Upload className={`w-8 h-8 mx-auto mb-2 ${dragOver ? "text-primary-500" : "text-slate-400"}`} />
          <p className="text-sm font-medium text-slate-600">
            {uploading ? "Uploading..." : "Drop files here or click to browse"}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            JPG, PNG, GIF, PDF up to {MAX_SIZE_MB}MB
          </p>
        </div>
      )}

      {/* File list */}
      {files && files.length > 0 && (
        <div className="space-y-2">
          {files.map((file) => (
            <div
              key={file.id}
              className="flex items-center gap-3 p-3 bg-white border border-slate-200 rounded-xl hover:shadow-sm transition-shadow"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                {isImage(file.mime_type) ? (
                  <Image className="w-5 h-5 text-slate-500" />
                ) : (
                  <FileText className="w-5 h-5 text-slate-500" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-700 truncate">
                  {file.original_filename}
                </p>
                <p className="text-xs text-slate-400">
                  {formatSize(file.file_size)} · {file.file_category}
                </p>
              </div>
              <div className="flex items-center gap-1">
                {isImage(file.mime_type) && (
                  <button
                    onClick={() => setPreviewFile(file)}
                    className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
                    title="Preview"
                  >
                    <Image className="w-4 h-4" />
                  </button>
                )}
                <a
                  href={getFileUrl(file.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
                  title="Download"
                >
                  <Download className="w-4 h-4" />
                </a>
                {!readOnly && (
                  <button
                    onClick={() => handleDelete(file.id)}
                    className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {(!files || files.length === 0) && readOnly && (
        <div className="flex items-center gap-2 text-sm text-slate-400 py-2">
          <AlertCircle className="w-4 h-4" />
          No files attached
        </div>
      )}

      {/* Image preview modal */}
      {previewFile && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
          onClick={() => setPreviewFile(null)}
        >
          <div className="relative max-w-3xl max-h-[85vh]">
            <button
              onClick={() => setPreviewFile(null)}
              className="absolute -top-10 right-0 p-2 text-white hover:text-slate-300 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={getFileUrl(previewFile.id)}
              alt={previewFile.original_filename}
              className="max-w-full max-h-[80vh] rounded-xl shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </div>
  );
}
