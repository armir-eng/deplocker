import { atomWithStorage } from "jotai/utils";

export const emailTaskIDAtom = atomWithStorage<string | null>(
  "email_task_id",
  null,
  undefined,
  { getOnInit: true },
);
