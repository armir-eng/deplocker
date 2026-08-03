import * as yup from "yup";

export const UserOrgs = yup.object().shape({
  user_id: yup.number().integer(),
  organizations: yup.array().of(yup.string()),
});
