const store = new Map();
module.exports = {
  set: (k, v) => store.set(k, v),
  get: (k) => store.get(k),
};
