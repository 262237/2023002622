# Stage 1 - Notification System Design

## Introduction

The objective of this notification platform is to help students receive updates related to placements, events and examination results. Since some notifications (especially placement drives) are time-sensitive, the system should support both normal REST APIs and real-time notification delivery.

## Main Features

* Create notifications
* View notifications
* View unread notifications
* Mark notification as read
* Mark all notifications as read
* Delete notification
* Get unread notification count
* Receive real-time notifications

---

## Notification Structure

```json
{
  "notificationId": "101",
  "userId": "2023002622",
  "title": "Placement Drive",
  "message": "XYZ company drive starts tomorrow",
  "type": "placement",
  "isRead": false,
  "createdAt": "2026-06-07T10:00:00Z"
}
```

---

## 1. Create Notification

### Endpoint

```http
POST /notifications
```

### Request

```json
{
  "userId": "2023002622",
  "title": "Placement Drive",
  "message": "XYZ company drive starts tomorrow",
  "type": "placement"
}
```

### Response

```json
{
  "notificationId": "101",
  "message": "Notification created"
}
```

---

## 2. Get All Notifications

### Endpoint

```http
GET /notifications/{userId}
```

### Response

```json
[
  {
    "notificationId": "101",
    "title": "Placement Drive",
    "isRead": false
  }
]
```

I chose a separate endpoint for fetching notifications because students may have hundreds of notifications and the frontend can load them whenever required.

---

## 3. Get Unread Notifications

### Endpoint

```http
GET /notifications/{userId}/unread
```

### Response

```json
[
  {
    "notificationId": "101",
    "title": "Placement Drive"
  }
]
```

---

## 4. Mark Notification As Read

### Endpoint

```http
PATCH /notifications/{notificationId}
```

### Request

```json
{
  "isRead": true
}
```

### Response

```json
{
  "message": "Notification updated"
}
```

---

## 5. Mark All Notifications As Read

### Endpoint

```http
PATCH /notifications/read-all/{userId}
```

### Response

```json
{
  "message": "All notifications marked as read"
}
```

---

## 6. Delete Notification

### Endpoint

```http
DELETE /notifications/{notificationId}
```

### Response

```json
{
  "message": "Notification deleted"
}
```

---

## 7. Unread Notification Count

### Endpoint

```http
GET /notifications/{userId}/count
```

### Response

```json
{
  "unreadCount": 5
}
```

This endpoint is useful for displaying notification badges without loading the complete notification list.

---

## Real-Time Notification Delivery

For real-time updates, WebSocket communication can be used.

### Connection

```http
ws://server/notifications
```

Whenever a new notification is created, the server pushes it directly to connected students.

### Example Event

```json
{
  "event": "new_notification",
  "notificationId": "101",
  "title": "Placement Drive",
  "message": "XYZ company drive starts tomorrow"
}
```

### Why WebSocket?

If the frontend repeatedly calls APIs every few seconds, it creates unnecessary server load. WebSocket allows the server to push updates immediately whenever a new notification is generated, providing a better user experience.

