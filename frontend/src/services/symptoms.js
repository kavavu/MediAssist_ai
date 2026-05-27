import api from "./api";

export const predictSymptoms = (symptomsText) =>
  api.post("/predict", { symptoms_text: symptomsText });

export const getModelInfo = () =>
  api.get("/model-info");
