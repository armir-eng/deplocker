import * as yup from "yup";

export const TaskStatusPollResponse = yup.object().shape({
  task_id: yup.string().required(),
  status: yup
    .string()
    .oneOf(["PENDING", "STARTED", "RETRY", "SUCCESS", "FAILURE"])
    .required(),
  result: yup.string().nullable(),
});
