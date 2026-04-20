export function AdminHome() {
  return (
    <div>
      <h1>Admin</h1>
      <p className="muted">
        Manage categories, parts, file uploads, and product drafts. Publishing still requires a valid
        snapshot payload (use the draft editor + publish JSON, or the OpenAPI docs for full control).
      </p>
      <ul>
        <li>
          <strong>Categories</strong> — create taxonomy (public list uses GET /categories).
        </li>
        <li>
          <strong>Parts</strong> — engineering parts; attach images via uploaded asset id.
        </li>
        <li>
          <strong>Uploads</strong> — SVG diagrams, PDFs, part photos (JPEG/PNG).
        </li>
        <li>
          <strong>Products</strong> — KMATs, draft JSON, optional publish body.
        </li>
      </ul>
    </div>
  );
}
