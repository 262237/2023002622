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

# Stage 3

## Analysis of Existing Query

```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt ASC;
```

The query is correct because it returns unread notifications of a particular student.
However, when the table grows to around 5,000,000 notifications, the query can become slow. The database may need to scan a large number of rows before finding the required records. Sorting by `createdAt` can also increase execution time if proper indexing is not available.

Another issue is the usage of `SELECT *`. It fetches all columns even if the application only requires a few fields. This increases data transfer and memory usage.

## Improvements

Instead of selecting all columns, only required columns can be fetched.

```sql
SELECT notificationID,
       title,
       message,
       createdAt
FROM notifications
WHERE studentID = 1042
  AND isRead = false
ORDER BY createdAt ASC;
```

A composite index can also be created:

```sql
CREATE INDEX idx_notifications_student_read_date
ON notifications(studentID, isRead, createdAt);
```

This allows the database to quickly locate unread notifications of a student and return them in the required order.

## Expected Cost

Without indexes, the query may perform close to O(n) scanning where n is the number of notifications.

With the composite index, lookup becomes much faster and usually depends on index traversal rather than scanning the full table.

## Should We Add Indexes On Every Column?

I do not think adding indexes on every column is a good idea.

Advantages:

* Faster reads for some queries.

Disadvantages:

* More storage space is required.
* Insert and update operations become slower.
* Many indexes may never be used.

Therefore indexes should be created based on actual query patterns instead of adding them everywhere.

## Query To Find Students Who Received Placement Notifications In Last 7 Days

```sql
SELECT DISTINCT studentID
FROM notifications
WHERE notificationType = 'Placement'
  AND createdAt >= NOW() - INTERVAL 7 DAY;
```

This query returns all unique students who received placement notifications during the last seven days.

## Conclusion

The main reason for the slowdown is the increase in data volume and the absence of suitable indexing. Using a composite index and avoiding unnecessary column selection can significantly improve performance while keeping storage overhead reasonable.

# Stage 4

## Performance Improvements

As the number of students increases, fetching notifications from the database on every page load is not a good idea. The database will receive too many requests and response time may increase.

One thing I would do is load notifications only when the user opens the notification section instead of loading them on every page. This can reduce many unnecessary database calls.

Another option is using Redis cache. Frequently accessed data such as unread notification count can be stored in cache. This will reduce pressure on the database.

**Advantage:** Faster response.

**Disadvantage:** Cache data may sometimes become outdated for a short time.

I would also use pagination. For example, instead of returning 500 notifications, return only the latest 20 and load more when needed.

This reduces network traffic and makes the application feel faster.

For real-time updates, WebSockets can be used. When a new notification is created, it can be pushed directly to the user instead of repeatedly checking the server.

The drawback is that maintaining WebSocket connections is a little more complex compared to normal REST APIs.

In my opinion, a combination of pagination, caching and WebSocket notifications would be enough for this system. It reduces database load while still providing a good user experience.

# Stage 5

## My Observation

The current logic looks simple but I don't think it will work well when 50,000 students need to be notified.

If the system sends email, saves data and pushes notification one by one, the whole process may take a long time. Also if email sending fails somewhere in the middle, some students may get the notification while others may not.

For example, if 200 email requests fail, we need a way to identify them and try again instead of running the entire process again.

## My Suggested Solution

I would separate notification creation from notification delivery.

When HR clicks "Notify All", the system should first create the notification record and then create jobs for each student. These jobs can be processed in the background.

### Revised Flow

```text id="knx4wo"
notifyAll(studentIds, message)

save notification details

for each student:
    create delivery job

background worker:

get next job

send email

send in-app notification

update delivery status
```

## Handling Failures

If email sending fails, I would not stop the entire process.

Instead:

* Mark the job as failed.
* Retry it a few times.
* Store failed jobs separately for later review.

This way the remaining students can still receive notifications.

## Database And Email

In my opinion, saving data to the database and sending emails should not happen in a single transaction.

Database operations are generally quick, but email delivery depends on an external service and can fail for many reasons.

Because of that, I would save the notification first and then let background workers handle email delivery.

## Stage 6

I used a simple priority based approach.

Placement notifications are given highest priority, followed by Result notifications and then Event notifications.

Priority values:
- Placement = 3
- Result = 2
- Event = 1

A score is calculated using both notification type and recency. Newer notifications get slightly higher preference when notifications have similar importance.

To get top 10 notifications, notifications are sorted based on score and first 10 records are returned.

If notifications keep coming continuously, maintaining a min heap of size 10 would be more efficient than sorting the entire list every time.

## Final Thoughts

For a small number of users, the original approach may work. But for 50,000 students I think using background jobs and retry mechanisms would be much more reliable and easier to manage.

## Stage 7

Frontend will be developed using React.

Pages:
1. Notifications Page
2. Priority Notifications Page

Features:
- View all notifications
- Filter by notification type
- Show read and unread notifications separately
- Display top priority notifications
- Responsive layout for desktop and mobile

The application will fetch notifications from the provided API using page, limit and notification_type query parameters.

