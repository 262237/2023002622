const TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiYXVkIjoiaHR0cDovLzIwLjI0NC41Ni4xNDQvZXZhbHVhdGlvbi1zZXJ2aWNlIiwiZW1haWwiOiJ2akBnaXRhbS5pbiIsImV4cCI6MTc4MDgxMTIzMSwiaWF0IjoxNzgwODEwMzMxLCJpc3MiOiJBZmZvcmQgTWVkaWNhbCBUZWNobm9sb2dpZXMgUHJpdmF0ZSBMaW1pdGVkIiwianRpIjoiOWFjYWYxMzgtYTE3NC00YzhhLTgyYTMtMjcwNDEwM2I4ODRkIiwibG9jYWxlIjoiZW4tSU4iLCJuYW1lIjoiaiB2YW5kYW5hIiwic3ViIjoiNGQ0NDU1OWQtYjk5Ni00ZWRhLWExOWEtNTBmYTk4NzhmYjhkIn0sImVtYWlsIjoidmpAZ2l0YW0uaW4iLCJuYW1lIjoiaiB2YW5kYW5hIiwicm9sbE5vIjoiMjAyMzAwMjYyMiIsImFjY2Vzc0NvZGUiOiJ3Z0t0Z1oiLCJjbGllbnRJRCI6IjRkNDQ1NTlkLWI5OTYtNGVkYS1hMTlhLTUwZmE5ODc4ZmI4ZCIsImNsaWVudFNlY3JldCI6ImVRRkRNVnpCSFhKTmNydFMifQ.zvgz5ir3LwvJOBAOnlTqbXhAgyR6N6l_zWxt2WSU5cc";

const priorityWeight = {
  Placement: 3,
  Result: 2,
  Event: 1
};

async function getNotifications() {
  const response = await fetch(
    "http://4.224.186.213/evaluation-service/notifications",
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${TOKEN}`
      }
    }
  );

  const data = await response.json();
  return data.notifications;
}

function getScore(notification) {
  const weight = priorityWeight[notification.Type] || 0;

  const now = new Date();
  const createdTime = new Date(notification.Timestamp);

  const ageHours = (now - createdTime) / (1000 * 60 * 60);

  return weight * 1000 - ageHours;
}

function getTopNotifications(notifications, n = 10) {
  return notifications
    .sort((a, b) => getScore(b) - getScore(a))
    .slice(0, n);
}

async function main() {
  try {
    const notifications = await getNotifications();

    const top10 = getTopNotifications(notifications, 10);

    console.log("Top 10 Priority Notifications:");
    console.log(top10);
  } catch (error) {
    console.log("Error:", error.message);
  }
}

main();
