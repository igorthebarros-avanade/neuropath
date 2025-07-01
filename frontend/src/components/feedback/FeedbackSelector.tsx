import certifications from "@/src/domain/constants/certifications";
import Select from "../global/Select";
import Link from "next/link";
import { Dispatch, FormEvent, SetStateAction, useEffect, useState } from "react";
import Loading from "../global/Loading";
import Button from "../global/Button";
import { useSearchParams } from "next/navigation";

type Props = {
    selectedExam: string
    setSelectedExam: Dispatch<SetStateAction<string>>
    setShowLoadingFeedback: Dispatch<SetStateAction<boolean>>
}

const container = `mb-8`
const inputs = `flex flex-col gap-4 items-center`
const link = `!underline`

export default function FeedbackSelector(props: Props){
    const searchParams = useSearchParams()
    const defaultExam = searchParams.get('exam') || ''

    const [examsWithAvailableFeedbacks, setExamsWithAvailableFeedbacks] = useState<string[]>([''])
    const [showLoadingResults, setShowLoadingResults] = useState(true)

    async function handleSubmit(e: FormEvent<HTMLFormElement>){
        e.preventDefault()
        props.setShowLoadingFeedback(true)
    }
    
    useEffect(() => {
        setExamsWithAvailableFeedbacks(
            certifications.filter(certification => localStorage.getItem(`simulationResults-${certification}`))
        )
    }, [])
    
    useEffect(() => {
        if(examsWithAvailableFeedbacks[0] != ''){
            props.setSelectedExam(
                examsWithAvailableFeedbacks.includes(defaultExam) ? defaultExam : examsWithAvailableFeedbacks[0]
            )
            setShowLoadingResults(false)
        }
    }, [examsWithAvailableFeedbacks])

    return(
        <form autoComplete="off" className={container} onSubmit={handleSubmit}>
            {examsWithAvailableFeedbacks.length > 0 ?
                <div className={inputs}>
                    <Select label="Exams with available feedbacks" options={examsWithAvailableFeedbacks.map(e => {
                        return {text: e, value: e}
                    })} setValue={props.setSelectedExam} value={props.selectedExam}/>

                    <Button isSubmit>Analyze results</Button>
                </div>
            :
                <p>
                    There are no exams with available feedbacks, go to the <Link className={link} href={'/simulation'}>Exam Simulation page</Link> and complete the simulation of the desired certification.
                </p>
            }

            {showLoadingResults ?
                <Loading text={'Fetching available results...'}/>
            : <></>}
        </form>
    )
}