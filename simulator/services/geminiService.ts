import { GoogleGenAI, Type } from "@google/genai";
import { BoxEntity, Size } from "../types";

// Initialize the client
// Note: In a real production app, ensure the key is valid.
// The component using this service should handle errors gracefully.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });

export const generateScenario = async (
  prompt: string,
  bounds: Size
): Promise<BoxEntity[]> => {
  try {
    const modelName = 'gemini-2.5-flash';
    
    const response = await ai.models.generateContent({
      model: modelName,
      contents: `
        Generate a JSON configuration for a 2D simulator.
        Canvas Size: ${bounds.width}x${bounds.height}.
        User Request: "${prompt}".
        
        Return a list of entities. Each entity should have:
        - id (string)
        - position (x, y) within bounds
        - velocity (x, y) typical range -2 to 2
        - size (width, height) typical range 20-50
        - color (hex string)
        - label (short string)

        Ensure the JSON is valid and matches the schema.
      `,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              id: { type: Type.STRING },
              position: {
                type: Type.OBJECT,
                properties: {
                  x: { type: Type.NUMBER },
                  y: { type: Type.NUMBER },
                }
              },
              velocity: {
                type: Type.OBJECT,
                properties: {
                  x: { type: Type.NUMBER },
                  y: { type: Type.NUMBER },
                }
              },
              size: {
                type: Type.OBJECT,
                properties: {
                  width: { type: Type.NUMBER },
                  height: { type: Type.NUMBER },
                }
              },
              color: { type: Type.STRING },
              label: { type: Type.STRING },
            }
          }
        }
      }
    });

    const text = response.text;
    if (!text) return [];
    
    const data = JSON.parse(text);
    return data as BoxEntity[];

  } catch (error) {
    console.error("Gemini generation failed:", error);
    throw error;
  }
};
