# Edge case: GET /stats when there are no students

## 1) The edge case you identified

**GET /stats with zero students in the database.**

The spec says GET /stats should return `count`, `average`, `min`, and `max` of all student marks. It does not define what to return when there are no students. In that situation:

- **count** is clearly 0.
- **average** would require dividing by zero if we used “sum of marks / count”, which is undefined and can cause errors.
- **min** and **max** are undefined when there is no data (no marks to take the minimum or maximum of).

So the edge case is: *how should the API behave when there are no students?*

## 2) How you have accounted for this in your implementation

When there are no students:

- **count** is set to `0`.
- **average** is set to `0` (so the response is always a valid number and no division by zero is performed).
- **min** and **max** are set to `null` to indicate “no data” rather than a numeric value.

Example response when the database has no students:

```json
{
  "count": 0,
  "average": 0,
  "min": null,
  "max": null
}
```

So the route always returns HTTP 200 with a consistent JSON shape. Clients can check `count === 0` (or `min === null` / `max === null`) to handle the empty case without hitting division-by-zero or missing keys.
