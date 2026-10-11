export function renderErrorPage(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>500 - Server Error</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #09090b;
      color: #fafafa;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .container {
      text-align: center;
      max-width: 420px;
      padding: 2rem;
    }
    h1 {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 0.75rem;
    }
    p {
      color: #a1a1aa;
      font-size: 0.875rem;
      line-height: 1.5;
      margin-bottom: 1.5rem;
    }
    a {
      display: inline-block;
      padding: 0.5rem 1rem;
      background-color: #fafafa;
      color: #09090b;
      border-radius: 0.375rem;
      font-size: 0.875rem;
      font-weight: 500;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Something went wrong</h1>
    <p>An unexpected server error occurred while rendering the page.</p>
    <a href="/">Return Home</a>
  </div>
</body>
</html>`;
}
