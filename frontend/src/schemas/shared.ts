import * as yup from "yup";

export const SuccessReponse = yup.object().shape({
  message: yup.string().required(),
});
