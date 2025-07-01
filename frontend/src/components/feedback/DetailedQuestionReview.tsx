import { useState } from "react"
import { Tooltip } from "react-tooltip"

type Props = {
    feedback: any
}

const container = `mb-8`
const title = `font-bold mb-4 text-[20px]`
const questions = `flex flex-col gap-4`
const card = `border-x-4 border-y-2 p-4 rounded-lg`
const questionCard = `cursor-pointer flex gap-4 items-center justify-between`
const answerCard = `overflow-hidden`
const answerCardTitle = `font-bold mb-1 text-[18px]`
const answerCardText = `mb-4 pl-2`

export default function DetailedQuestionReview(props: Props){
    return (
        <section className={container}>
            <Tooltip id="tooltip" style={{backgroundColor: 'var(--color-a-darkOrange)'}}/>

            <h2 className={title}>Detailed question review</h2>

            <div className={questions}>
                {props.feedback.feedbackReport.detailedQuestionReview.map((question: any, index: number) => {
                    const accuracyPercent = Number(question[3].replace('%', ''))
                    const borderColor = accuracyPercent < 50 ? 'red' : accuracyPercent < 90 ? 'yellow' : 'green'
                    const [isOpen, setIsOpen] = useState(false)

                    return (
                        <div className={card} style={{borderColor: borderColor}} key={question[1].replaceAll(' ', '')}>
                            <div className={questionCard} onClick={() => setIsOpen(!isOpen)}>
                                <p className="text-[18px]">{index + 1}.</p>

                                <p className="font-bold grow text-[20px]">{question[1]}</p>

                                {isOpen ?
                                    <i className="ri-arrow-up-s-line text-[22px]"></i>
                                :
                                    <i className="ri-arrow-down-s-line text-[22px]"></i>
                                }
                            </div>

                            <div className={`${answerCard} ${isOpen ? 'border-t' : ''}`} style={{
                                borderColor: borderColor,
                                height: isOpen ? 'unset' : '0', 
                                opacity: isOpen ? '100%' : '0%',
                                marginTop: isOpen ? '1rem' : '0',
                                paddingTop: isOpen ? '1rem' : '0'
                            }}>
                                <h3 className={answerCardTitle}>Your answer:</h3>
                                <p className={answerCardText}>{question[2]}</p>
                                
                                {question[0] != 'Yes No' ?
                                    <>
                                    <h3 className={answerCardTitle}>Accuracy percentage:</h3>
                                    <p className={answerCardText}>{question[3]}</p>
                                    </>
                                : <></>}
                                
                                <h3 className={answerCardTitle}>Answer feedback:</h3>
                                <p className={answerCardText}>{question[4]}</p>
                            </div>
                        </div>
                    )
                })}
            </div>
        </section>
    )
}