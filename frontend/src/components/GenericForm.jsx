import { useState } from "react";
import FeedbackAlert from "./FeedbackAlert";
import PropTypes from "prop-types";


export default function GenericForm({controls, onSubmit, submitBtnLabel, submitSuccessMsg, helperText}) {
    const [formState, setFormState] = useState({
        "isSubmitting": false,
        "error": "",
        "isSuccessful": false
    });
    const [canShowFeedback, setCanShowFeedback] = useState(false);

    const controlsTransformed = controls.map((element, idx) => {
        let FormControl;

        switch(element.type) {
            case "text":
            case "number":
            case "email":
                FormControl = (
                    <input
                        type={element.type}
                        value={element.value}
                        required={!!element.required}
                        onChange={element.onValueChange}
                        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    />
                );

                break;
            default:
                throw new EvalError(`Error in creating form. Unidentifiable element type (${element.type})`);
        }

        return (
            <div className="space-y-2" key={`key-${idx}`}>
                <label className="text-sm font-semibold text-slate-700">
                    {element.label}
                </label>

                {FormControl}
            </div>
        );
    });


    async function localOnSubmitWrapper(event) {
        event.preventDefault();
        setCanShowFeedback(false);

        try {
            setFormState(prevState => ({...prevState, "error":"", "isSubmitting": true}));
            await onSubmit(event);
            setFormState(prevState => ({...prevState, "isSuccessful": true}));
        } catch(submitError) {
            setFormState(prevState => ({...prevState, "error": submitError.message || "Form Submission Failed"}));
        } finally {
            setFormState(prevState => ({...prevState, "isSubmitting": false}));
            setCanShowFeedback(true);
        }
    }


    return (
        <form onSubmit={localOnSubmitWrapper} className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-6">
            {controlsTransformed}

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-slate-500">{helperText || "Submit the Form"}</p>
                <button
                    type="submit"
                    disabled={formState.isSubmitting}
                    className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                    {formState.isSubmitting ? "Submitting form..." : submitBtnLabel}
                </button>
            </div>

            {(canShowFeedback && formState.error) ? <FeedbackAlert kind="error" message={formState.error} /> : null}
            {(canShowFeedback && formState.isSuccessful && ( ! formState.error)) ? <FeedbackAlert kind="success" message={submitSuccessMsg} /> : null}
        </form>
    );
}

GenericForm.propTypes = {
    "controls": PropTypes.array.required,
    "onSubmit": PropTypes.func.required,
    "submitBtnLabel": PropTypes.string.required,
    "submitSuccessMsg": PropTypes.string.required,
    "helperText": PropTypes.string
}