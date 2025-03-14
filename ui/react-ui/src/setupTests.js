// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Add custom matchers
expect.extend({
  toBeRequired(received) {
    const pass = received.hasAttribute('required');
    if (pass) {
      return {
        message: () => `expected ${received} not to be required`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be required`,
        pass: false,
      };
    }
  },
}); 