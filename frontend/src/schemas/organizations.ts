import * as z from "zod";

export const UserOrgs = z.object({
  user_id: z.number().int().optional(),
  organizations: z.array(z.string()).optional(),
});
