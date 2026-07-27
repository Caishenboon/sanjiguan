import type { Preview } from "@storybook/react-vite";
import "../src/tokens.css";

const preview: Preview = {
  parameters: {
    a11y: { test: "error" },
    backgrounds: {
      default: "ink",
      values: [
        { name: "ink", value: "#080b12" },
        { name: "moon", value: "#f2efe7" },
      ],
    },
  },
};
export default preview;
