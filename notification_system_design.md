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

# Stage 2 - Database Design

## Database Selection

For storing notifications, I would use PostgreSQL.

I selected PostgreSQL because the data in this application is structured and most operations are simple database queries like fetching notifications, getting unread notifications and updating notification status. PostgreSQL also supports indexing which can help improve performance when the number of notifications increases.

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100)
);
```

### Notifications Table

```sql
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    title VARCHAR(255),
    message TEXT,
    notification_type VARCHAR(20),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

The users table stores student details and the notifications table stores all notifications sent to students.

---

## Queries Based On Stage 1 APIs

### Get All Notifications

```sql
SELECT *
FROM notifications
WHERE user_id = '2023002622'
ORDER BY created_at DESC;
```

### Get Unread Notifications

```sql
SELECT *
FROM notifications
WHERE user_id = '2023002622'
AND is_read = FALSE
ORDER BY created_at DESC;
```

### Mark Notification As Read

```sql
UPDATE notifications
SET is_read = TRUE
WHERE notification_id = 101;
```

### Mark All Notifications As Read

```sql
UPDATE notifications
SET is_read = TRUE
WHERE user_id = '2023002622';
```

### Delete Notification

```sql
DELETE FROM notifications
WHERE notification_id = 101;
```

### Get Unread Notification Count

```sql
SELECT COUNT(*)
FROM notifications
WHERE user_id = '2023002622'
AND is_read = FALSE;
```

---

## Problems When Data Increases

As more students start using the system, the number of notifications will increase very quickly.

Some possible problems are:

* Notification fetching can become slower.
* Unread notification queries may take more time.
* Database size will keep growing.
* Many users accessing notifications at the same time can increase database load.

---

## Solutions

To handle these problems, I would use the following approaches:

* Create indexes on user_id, is_read and created_at.
* Use pagination instead of loading all notifications together.
* Archive very old notifications if they are no longer needed.
* Cache frequently used data such as unread notification count.

These changes can help maintain good performance even when the system stores a large number of notifications.

## Conclusion

PostgreSQL is a suitable choice for this application because it works well with structured data and supports efficient querying. Using indexes, pagination and caching can help the system scale as the number of users and notifications increases.

