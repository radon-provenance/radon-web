module.exports = {
  branches: ["main"],
  plugins: [
    ["@semantic-release/commit-analyzer", {
      parserOpts: {
        headerPattern: /^(\w*!?)(?:\((.*)\))?: (.*)$/,
        headerCorrespondence: ['type', 'scope', 'subject'],
      },
      releaseRules: [
        { type: "feat!", release: "major" },
        { type: "fix!", release: "major" },
        { type: "feat", release: "minor" },
        { type: "fix", release: "patch" },
        { type: "perf", release: "patch" }
      ]
    }],
    "@semantic-release/release-notes-generator",
    ["@semantic-release/exec", {
      "prepareCmd": "echo ${nextRelease.version} > VERSION" 
    }],
    ["@semantic-release/git", {
      "assets": ["VERSION"],
      "message": "chore(release): ${nextRelease.version} [skip ci]"
    }],
    "@semantic-release/github"
  ]
};