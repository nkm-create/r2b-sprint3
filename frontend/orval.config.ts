export default {
  api: {
    input: {
      target: '../backend/openapi.json',
    },
    output: {
      target: './src/lib/api/generated.ts',
      client: 'react-query',
      httpClient: 'fetch',
      clean: true,
      prettier: true,
    },
  },
};
