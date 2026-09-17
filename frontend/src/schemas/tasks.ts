import * as z from "zod";

export const TaskStatusPollResponse = z.object({
  task_id: z.string().min(1),
  status: z.enum(["PENDING", "STARTED", "RETRY", "SUCCESS", "FAILURE"]),
  result: z.string().nullable().optional(),
});
