# Deep Insight Backend Tests

Note: If you encounter problems with the node version, you may need to update to the latest version (at least node 22). If you have nvm installed, you can run the following command:
`nvm install node --reinstall-packages-from=$(nvm current) && nvm alias default node`

Tests are organized into two types:
- **`/unit`** - Fast unit tests using TestClient (no live server)
- **`/live`** - Integration tests with actual backend server

```bash
# Run all tests
npm run test

# Run only unit tests (fast)
npm run test:unit

# Run only live tests (slower, full integration)
npm run test:live

# Run with verbose output
npm run test:verbose

# Run specific employee tests
npm run test:employee

# Watch tests for changes
npm run test:unit:watch
npm run test:live:watch
```
