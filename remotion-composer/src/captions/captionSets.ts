/** Pure caption-set timing math — extracted so tests can drive the real
 * decision logic in node instead of grepping JSX. */

/** Words per caption set: a set appears, holds, disappears, then the next set
 * takes its place — small transient groups instead of one persistent box. */
export const WORDS_PER_SET = 4;

export interface CaptionSetState {
  /** Which set of words is on screen (0-based). */
  setIndex: number;
  /** Index of the set's first word in the full text. */
  setStart: number;
  /** The words this set displays. */
  setWords: string[];
  /** Index of the currently-emphasised word inside the set. */
  activeInSet: number;
  /** 0 = invisible (set-boundary breath), 1 = fully held. */
  opacity: number;
}

const clamp01 = (v: number): number => Math.min(1, Math.max(0, v));

/** Which caption set is on screen at `progress` (0..1 of the spoken text),
 * and its fade opacity.
 *
 * The set window is anchored to WORD positions: set k owns progress in
 * [setStart / wordCount, (setStart + setWords.length) / wordCount), which is
 * exactly the range of progress that maps to its word indices. Anchoring the
 * window to setIndex / setCount instead misaligns whenever the word count is
 * not divisible by WORDS_PER_SET (the final set is partial): the active word
 * then falls outside its own set's window, local clamps to 1 and the opacity
 * dies — hiding the caption for up to ~0.6s mid-scene. Word-anchored windows
 * make the invisible region exactly the designed breath at each boundary. */
export const captionSetAt = (text: string, progress: number): CaptionSetState | null => {
  const allWords = text.split(/\s+/).filter(Boolean);
  if (allWords.length === 0) {
    return null;
  }
  const setCount = Math.ceil(allWords.length / WORDS_PER_SET);
  const activeWordIdx = Math.min(allWords.length - 1, Math.floor(progress * allWords.length));
  const setIndex = Math.min(setCount - 1, Math.floor(activeWordIdx / WORDS_PER_SET));
  const setStart = setIndex * WORDS_PER_SET;
  const setWords = allWords.slice(setStart, setStart + WORDS_PER_SET);

  const p0 = setStart / allWords.length;
  const p1 = (setStart + setWords.length) / allWords.length;
  const local = clamp01((progress - p0) / Math.max(1e-9, p1 - p0));
  const opacity = Math.max(0, Math.min(1, local / 0.12, (1 - local) / 0.12));

  return {setIndex, setStart, setWords, activeInSet: activeWordIdx - setStart, opacity};
};
