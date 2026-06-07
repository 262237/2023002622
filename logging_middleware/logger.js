import { TOKEN } from "./config.js";

export async function Log(stack, level, packageName, message) {
  try {
    const response = await fetch(
      "http://4.224.186.213/evaluation-service/logs",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${TOKEN}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          stack,
          level,
          package: packageName,
          message
        })
      }
    );

    return await response.json();
  } catch (error) {
    return {
      error: error.message
    };
  }
}
